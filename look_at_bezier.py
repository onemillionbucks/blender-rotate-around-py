# Purpose, lock a camera to a bezier curve
# Camera rotates and locks to target "Suzanne", and renders 8 images from the circle
# Sometimes rotating a mesh just wont work. Use this if rotate_around doesnt rotate effectively.
# Instead the camera is moved along a bezier circle. Only drawback is that shadows wont look right
# unless you also move the sun direction as part of this script. The script doesnt yet handle this.

import bpy
import math
import os

class LookAtCamera(bpy.types.Operator):
    bl_idname = "render.image_around"
    bl_label = "Rotate 360 and Take 8 Pictures"

    def execute(self, context):
        # DESELECT ALL
        bpy.ops.object.select_all(action='DESELECT')

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

        # DESELECT ALL
        bpy.ops.object.select_all(action='DESELECT')

        # Create a Bezier Circle for the camera to be fixed on
        try:
            bezierCircle = bpy.data.objects['BézierCircle']

            bezierCircle.select_set(True)
            bpy.ops.object.delete()
        except KeyError:
            print("Creating BézierCircle")

        bpy.ops.curve.primitive_bezier_circle_add(radius=4.0,
         enter_editmode=False, align='WORLD',
          location=(0.0, 0.0, 6.0),
           rotation=(0.0, 0.0, math.pi), # 180 degrees so that we start facing front
            scale=(6.0, 6.0, 6.0))

        bezierCircle = bpy.data.objects["BézierCircle"]
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

        lockTargetObj = bpy.data.objects["Suzanne"]
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
        output_dir = "/Users/sebastiandetering/pdev/blender-api/outputs"
        output_file_pattern_string = 'suzanne%d.jpg'

        if not os.path.exists(output_dir):
            print("creating output directory.")
            os.mkdir(output_dir)


        # Rendering 8 images
        # X Position on path is from 0 - 10 for some reason

        for i in range(8):
            bpy.context.scene.render.filepath = os.path.join(output_dir, (output_file_pattern_string % i))
            cam.location.x = i * 10/8
            bpy.ops.render.opengl(write_still=True, view_context=False)

        print("Saved images to: " + output_dir)
        return {'FINISHED'}


bpy.utils.register_class(LookAtCamera)
