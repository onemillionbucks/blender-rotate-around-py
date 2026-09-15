# Purpose, lock a camera to a bezier curve
# Camera rotates and locks to target "Suzanne", and renders 8 images from the circle
# Sometimes rotating a mesh just wont work. Use this if rotate_around doesnt rotate effectively.
# Instead the camera is moved along a bezier circle. Only drawback is that shadows wont look right
# unless you also move the sun direction as part of this script. The script doesnt yet handle this.

import bpy
import math
import os

## SET YOUR OUTPUT DIR HERE
OUTPUT_DIR_WINDOWS = os.path.join('B:', '\Models', 'Rotated Images')
LINUX_USER = "Seb"
OUTPUT_DIR_MAC_OR_LINUX = os.path.join('Users', LINUX_USER, 'Documents', 'Rotated Images')

BEZIER_CIRCLE_RADIUS=10.0
IMAGE_COUNT=8
TARGET_OBJECT="Suzanne"

class LookAtCamera(bpy.types.Operator):
    bl_idname = "render.image_around"
    bl_label = "Rotate 360 and Take 8 Pictures"
    output_dir = ""

    def execute(self, context):
        # DESELECT ALL
        bpy.ops.object.select_all(action='DESELECT')

        self.set_operating_system_output_directory()

        # select camera, delete it, make a fresh one.
        try:
            cam = bpy.data.objects["Camera"]

            cam.select_set(True)
            bpy.ops.object.delete()
        except KeyError:
            print("Creating camera.")

        bpy.ops.object.camera_add()
        cam = bpy.data.objects["Camera"]
        context.scene.camera = cam
        # https://blender.stackexchange.com/questions/30643/how-to-toggle-to-camera-view-via-python
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                break
        # DESELECT ALL
        bpy.ops.object.select_all(action='DESELECT')

        # Create a Bezier Circle for the camera to be fixed on
        try:
            bezierCircle = bpy.data.objects['BezierCircle']
            print("Recreating the bezier circle")
            bezierCircle.select_set(True)
            bpy.ops.object.delete()
        except KeyError:
            print("Creating BézierCircle")

        bpy.ops.curve.primitive_bezier_circle_add(radius=BEZIER_CIRCLE_RADIUS,
         enter_editmode=False, align='WORLD',
          location=(0.0, 0.0, BEZIER_CIRCLE_RADIUS),
           rotation=(0.0, 0.0, math.pi), # 180 degrees so that we start facing front
            scale=(1.0, 1.0, 1.0))

        bezierCircle = bpy.data.objects["BezierCircle"]
        # DESELECT ALL
        bpy.ops.object.select_all(action='DESELECT')

        # Set CLAMP_TO constraint on Camera(active+selected)
        cam.select_set(True)
        context.view_layer.objects.active = cam

        # BézierCircle (selected for constraint target)
        bezierCircle.select_set(True)

        bpy.ops.object.constraint_add_with_targets(type='CLAMP_TO')
        # So we can use X Periodically to move around the circle
        context.object.constraints["Clamp To"].use_cyclic = True

        # DESELECT ALL
        bpy.ops.object.select_all(action='DESELECT')

        # Object (selected for Lock Track target)
        cam.select_set(True)

        lockTargetObj = bpy.data.objects[TARGET_OBJECT]
        lockTargetObj.select_set(True)

        bpy.ops.object.constraint_add_with_targets(type="LOCKED_TRACK")
        context.object.constraints["Locked Track"].track_axis = "TRACK_Y"
        context.object.constraints["Locked Track"].lock_axis = "LOCK_Z"

        # Repeat for -Z, X locked track
        bpy.ops.object.constraint_add_with_targets(type="LOCKED_TRACK")
        context.object.constraints["Locked Track.001"].track_axis = "TRACK_NEGATIVE_Z"
        context.object.constraints["Locked Track.001"].lock_axis = "LOCK_X"
        bpy.context.view_layer.update()

        bpy.ops.render.view_show()

        bpy.context.scene.render.filepath

        output_file_pattern_string = TARGET_OBJECT + '_%d.png'

        # Rendering images
        # X position is the only thing that maps a locked track, with the setup we have here it goes from
        # X = 1.5 * BEZIER_CIRCLE_RADIUS -> 0
        # X = -0.5 * BEZIER_CIRCLE_RADIUS -> 2PI
        for i in range(IMAGE_COUNT):
            bpy.context.scene.render.filepath = os.path.join(self.output_dir, (output_file_pattern_string % i))
            cam.location.x = 1.5 * BEZIER_CIRCLE_RADIUS - 2 * BEZIER_CIRCLE_RADIUS * (i / IMAGE_COUNT)
            bpy.ops.render.render(write_still=True, use_viewport=True)

        print("Saved images to: " + self.output_dir)
        return {'FINISHED'}

    def set_operating_system_output_directory(self):
        if os.name == 'nt':
            self.output_dir = OUTPUT_DIR_WINDOWS
        else:
            self.output_dir = OUTPUT_DIR_MAC_OR_LINUX


        print(self.output_dir)

        if not os.path.exists(self.output_dir):
            print("creating output directory.")
            os.mkdir(self.output_dir)

bpy.utils.register_class(LookAtCamera)
