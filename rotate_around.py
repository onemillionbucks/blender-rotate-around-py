import bpy
import math
import mathutils
import os

# Purpose, camera locks to target
# Object rotates for each render, saves output
# IMPORTANT after running this file: bpy.ops.render.image_around()
## SET YOUR OUTPUT DIR HERE
OUTPUT_DIR_WINDOWS = os.path.join('B:', '\Models', 'Rotated Images')
LINUX_USER = "Seb"
OUTPUT_DIR_MAC_OR_LINUX = os.path.join('Users', LINUX_USER, 'Documents', 'Rotated Images')

# ('BLENDER_EEVEE', 'BLENDER_WORKBENCH', 'CYCLES', Optional: 'BLENDER_EVEE_NEXT')
RENDER_ENGINE = 'BLENDER_EEVEE'
CAMERA_RESOLUTION=[64,64]
### ENUM "IMAGE_FIRST_OBJECT_IN_COLLECTION", "IMAGE_ALL_MESHES" <- default
# "IMAGE_FIRST_OBJECT_IN_COLLECTION" <- use this if you have a collection
# with several meshes that make up a model to be imaged

COLLECTION_IMAGING_MODE="IMAGE_FIRST_OBJECT_IN_COLLECTION"
print("bpy.ops.render.image_around() is now ready to run")

# Adjust to ensure object is in frame
CAMERA_OFFSET_VECTOR = [0.0, -5.0, 5.0]

class LookAtCamera(bpy.types.Operator):
    bl_idname = "render.image_around"
    bl_label = "Rotate Object 360 and Take 8 Pictures"
    
    camera_name="Rotation Imaging Camera"
    output_dir = ""
    mesh_objects = []
    original_object_matrix = []
    
    def execute(self, context):
        self.set_operating_system_output_directory()
        
        print("IMPORTANT: make sure your view is bound to the camera...") # Couldnt find the api for this
        # set the render engine to workbench
        context.scene.render.engine = RENDER_ENGINE
    
        if COLLECTION_IMAGING_MODE == "IMAGE_FIRST_OBJECT_IN_COLLECTION":
            self.fetch_first_mesh_in_each_collection()
        else:
            self.fetch_all_meshes()

        for m in self.mesh_objects:
            self.refreshCamThenTarget(context, m)
            self.renderTarget(context, m)
        
        print("Saved images to: " + self.output_dir)

        self.cleanup()
        return {'FINISHED'}
    
    def fetch_first_mesh_in_each_collection(self):
        # find collections with meshes
        if len(bpy.data.collections) > 0:
            for col in bpy.data.collections:
                if len(col.objects) > 0:
                    found_mesh = False
                    for o in col.objects:
                        if o.type == 'MESH':
                            print("using first mesh ", o, " found in collection ", col)
                            self.mesh_objects.append(o)
                            found_mesh = True
                            break
                    if not found_mesh:
                        print("No mesh found in collection", col)
                else:   
                    print("Empty collection", col)
        else:
            print('NO COLLECTIONS')
            
    def fetch_all_meshes(self):
        # find all the objects that are meshes to capture
        for o in context.scene.objects:
            print(o.type)
            if o.type != 'MESH':
                continue
            self.mesh_objects.append(o)
            
    def set_operating_system_output_directory(self):
        if os.name == 'nt':
            self.output_dir = OUTPUT_DIR_WINDOWS
        else:
            self.output_dir = OUTPUT_DIR_MAC_OR_LINUX
        

        print(self.output_dir)
        
        if not os.path.exists(self.output_dir):
            print("creating output directory.")
            os.mkdir(self.output_dir)
    
    def renderTarget(self, context, tgtObject):
        output_file_pattern_string = tgtObject.name + '%d.jpg'
        
        original_rotation_z = tgtObject.rotation_euler.z
        tgtObject.rotation_euler.z = 0.0
        imgCount = 8
        for i in range(imgCount):
            tgtObject.rotation_euler.z = i * 2 * math.pi / imgCount
            bpy.context.scene.render.filepath = os.path.join(self.output_dir, (output_file_pattern_string % i))
            
            bpy.ops.render.render(write_still=True, use_viewport=True)

        tgtObject.rotation_euler.z = original_rotation_z
        print("done rendering " + output_file_pattern_string)
        
        
    def refreshCamThenTarget(self, context, tgtObject):
         # DESELECT ALL, so we can set the camera name after adding to scene
        bpy.ops.object.select_all(action='DESELECT')
        
        # select camera, or create it
        cam = ""
        try:
            cam = bpy.data.objects[self.camera_name]
        except KeyError:
            print("Creating a new",self.camera_name)
            bpy.ops.object.camera_add()
            context.selected_objects[0].name = self.camera_name 
            cam = bpy.data.objects[self.camera_name]
            
        context.scene.camera = cam

        context.scene.render.resolution_x = CAMERA_RESOLUTION[0]
        context.scene.render.resolution_y = CAMERA_RESOLUTION[1]
        
        cam.location = mathutils.Vector(CAMERA_OFFSET_VECTOR) + tgtObject.location.xyz
        
        # DESELECT ALL again
        bpy.ops.object.select_all(action='DESELECT')
        # Object (selected for Lock Track target)
        cam.select_set(True)
        tgtObject.select_set(True)
        
        bpy.ops.object.constraint_add_with_targets(type="LOCKED_TRACK")
        context.object.constraints["Locked Track"].track_axis = "TRACK_Y"
        context.object.constraints["Locked Track"].lock_axis = "LOCK_Z"
    
        # Repeat for -Z, X locked track
        bpy.ops.object.constraint_add_with_targets(type="LOCKED_TRACK")
        context.object.constraints["Locked Track.001"].track_axis = "TRACK_NEGATIVE_Z"
        context.object.constraints["Locked Track.001"].lock_axis = "LOCK_X"

        # https://blender.stackexchange.com/questions/30643/how-to-toggle-to-camera-view-via-python
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                break

    def cleanup(self):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[self.camera_name].select_set(True)
        bpy.ops.object.delete()
        
        

bpy.utils.register_class(LookAtCamera)