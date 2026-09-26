extends SceneTree
## Original, asset-free process-isolation fixture; not an AI agent or a game.
var body: RigidBody3D
var scene: Node3D
var config: Dictionary
var output: String
var ticks: int = 0
var contacts: int = 0
var early_y: float = NAN
var early_x: float = NAN
var started: bool = false
var finished: bool = false
var elapsed: float = 0.0
var active_clock: int = 0
var active_epoch_usec: int = 0

func _initialize() -> void:
	call_deferred("_setup")

func _write(path: String, data: Variant) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("Cannot create owned result file")
		quit(2)
		return
	f.store_string(JSON.stringify(data))
	f.close()

func _setup() -> void:
	output = OS.get_environment("PROBE_OUTPUT")
	config = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("PROBE_CONFIG")))
	if output.is_empty() or config.is_empty():
		quit(2)
		return
	scene = Node3D.new()
	root.add_child(scene)
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color(0.03, 0.04, 0.07)
	scene.add_child(environment)
	if config["floor"]:
		var floor_body := StaticBody3D.new()
		floor_body.position.y = -0.25
		var floor_shape := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(2000, 0.5, 2000)
		floor_shape.shape = box
		floor_body.add_child(floor_shape)
		scene.add_child(floor_body)
		var floor_mesh := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		mesh.size = box.size
		floor_mesh.mesh = mesh
		floor_body.add_child(floor_mesh)
	body = RigidBody3D.new()
	body.freeze = true
	body.position = Vector3(0, 3, 0)
	body.gravity_scale = float(config["gravity"]) / 9.8
	body.linear_damp_mode = RigidBody3D.DAMP_MODE_REPLACE
	body.linear_damp = 0.0
	body.contact_monitor = true
	body.max_contacts_reported = 4
	body.body_entered.connect(func(_b: Node) -> void: contacts += 1)
	var shape := CollisionShape3D.new()
	var sphere := SphereShape3D.new()
	sphere.radius = 0.25
	shape.shape = sphere
	body.add_child(shape)
	var visual := MeshInstance3D.new()
	var ball_mesh := SphereMesh.new()
	ball_mesh.radius = 0.25
	ball_mesh.height = 0.5
	visual.mesh = ball_mesh
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color.from_hsv(float(config["hue"]), 0.85, 1.0)
	visual.material_override = material
	body.add_child(visual)
	scene.add_child(body)
	var camera := Camera3D.new()
	camera.position = Vector3(6, 5, 8)
	scene.add_child(camera)
	camera.look_at(Vector3(1.5, 1, 0))
	camera.current = true
	_write("user://worker.json", {"id": config["id"]})
	_write(output.path_join("ready.json"), {"id": config["id"], "pid": OS.get_process_id(), "user_dir": OS.get_user_data_dir()})

func _process(_delta: float) -> bool:
	if config.is_empty() or started or finished:
		return false
	if FileAccess.file_exists(output.path_join("go")):
		started = true
		active_clock = Time.get_ticks_usec()
		active_epoch_usec = int(Time.get_unix_time_from_system() * 1000000.0)
		body.freeze = false
		body.linear_velocity = Vector3(float(config["speed"]), 0, 0)
		_write(output.path_join("started.json"), {"id": config["id"], "pid": OS.get_process_id()})
	return false

func _physics_process(delta: float) -> bool:
	if not started or finished:
		return false
	ticks += 1
	elapsed += delta
	if ticks == 30:
		early_y = body.position.y
		early_x = body.position.x
	if ticks % 30 == 0:
		_write(output.path_join("progress.json"), {"id": config["id"], "ticks": ticks})
	if ticks >= int(config["frames"]):
		finished = true
		body.freeze = true
		call_deferred("_finish")
	return false

func _finish() -> void:
	var report := {"schema": 1, "completed": true, "config": config,
		"engine": Engine.get_version_info()["string"], "pid": OS.get_process_id(),
		"display": DisplayServer.get_name(), "renderer": RenderingServer.get_current_rendering_method(),
		"ticks": ticks, "simulation_seconds": elapsed, "active_wall_ms": (Time.get_ticks_usec() - active_clock) / 1000.0,
		"active_start_unix_usec": active_epoch_usec,
		"active_finish_unix_usec": int(Time.get_unix_time_from_system() * 1000000.0),
		"contacts": contacts, "early_y": early_y, "early_x": early_x,
		"final_y": body.position.y, "final_x": body.position.x,
		"checks": {}, "capture": null}
	# Loose physical tolerance accommodates one tick of callback ordering; not a pixel oracle.
	var expected_y: float = 3.0 - 0.5 * float(config["gravity"]) * 0.5 * 0.5
	report["checks"] = {
		"completed_ticks": ticks == int(config["frames"]),
		"gravity_response": is_finite(early_y) and absf(early_y - expected_y) < 0.2,
		"lateral_response": is_finite(early_x) and absf(early_x - float(config["speed"]) * 0.5) < 0.1,
		"floor_contact": contacts > 0,
		"rests_above_floor": body.position.y > 0.15 and body.position.y < 0.4,
		"owned_user_state": JSON.parse_string(FileAccess.get_file_as_string("user://worker.json"))["id"] == config["id"]}
	if config["render"]:
		await process_frame
		await RenderingServer.frame_post_draw
		var image: Image = root.get_texture().get_image()
		var valid: bool = image != null and not image.is_empty() and image.get_size() == Vector2i(320, 240)
		report["checks"]["pixel_readback"] = valid
		report["adapter"] = RenderingServer.get_video_adapter_name()
		report["checks"]["software_renderer"] = "llvmpipe" in report["adapter"].to_lower()
		if valid:
			var filename := output.path_join("frame.png")
			report["checks"]["png_saved"] = image.save_png(filename) == OK
			report["capture"] = {"file": "frame.png", "sha256": FileAccess.get_sha256(filename), "width": image.get_width(), "height": image.get_height()}
	_write(output.path_join("result.json"), report)
	print("PROBE_RESULT " + JSON.stringify({"id": config["id"], "ticks": ticks, "checks": report["checks"]}))
	quit(0 if report["checks"].values().all(func(v): return v == true) else 1)
