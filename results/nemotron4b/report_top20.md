### eval_id-stack-0 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.26, location=(-2.09, 1.31, 0.63))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Ball cube on top of Marble
ball_location = (marble.location.x, marble.location.y, marble.location.z + 0.63 + 0.345)
bpy.ops.mesh.primitive_cube_add(size=0.69, location=ball_location)
ball = bpy.context.active_object
ball.name = "Ball"
```

### eval_id-stack-0 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.26, location=(-2.09, 1.31, 0.63))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Ball cube on top of Marble
ball_location = (marble.location.x, marble.location.y, marble.location.z + 0.63 + 0.345)
bpy.ops.mesh.primitive_cube_add(size=0.69, location=ball_location)
ball = bpy.context.active_object
ball.name = "Ball"
```

### eval_id-stack-0 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.26, location=(-2.09, 1.31, 0.63))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Ball cube on top of Marble
ball_location = (marble.location.x, marble.location.y, marble.location.z + 0.63 + 0.345)
bpy.ops.mesh.primitive_cube_add(size=0.69, location=ball_location)
ball = bpy.context.active_object
ball.name = "Ball"
```

### eval_id-stack-0 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.26, location=(-2.09, 1.31, 0.63))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Ball cube on top of Marble
ball_location = (marble.location.x, marble.location.y, marble.location.z + 0.63 + 0.345)
bpy.ops.mesh.primitive_cube_add(size=0.69, location=ball_location)
ball = bpy.context.active_object
ball.name = "Ball"
```

### eval_id-stack-0 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create "Marble" cube
bpy.ops.mesh.primitive_cube_add(size=1.26, location=(-2.09, 1.31, 0.63))
marble = bpy.context.active_object
marble.name = "Marble"

# Create "Ball" cube on top of "Marble"
ball_location = (marble.location.x, marble.location.y, marble.location.z + 0.63 + 0.345)
bpy.ops.mesh.primitive_cube_add(size=0.69, location=ball_location)
ball = bpy.context.active_object
ball.name = "Ball"
```

### eval_id-stack-0 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.26, location=(-2.09, 1.31, 0.63))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Ball cube on top of Marble
ball_location = (marble.location.x, marble.location.y, marble.location.z + 0.63 + 0.345)
bpy.ops.mesh.primitive_cube_add(size=0.69, location=ball_location)
ball = bpy.context.active_object
ball.name = "Ball"
```

### eval_id-stack-0 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.26, location=(-2.09, 1.31, 0.63))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Ball cube on top of Marble
ball_location = (marble.location.x, marble.location.y, marble.location.z + 0.63 + 0.345)
bpy.ops.mesh.primitive_cube_add(size=0.69, location=ball_location)
ball = bpy.context.active_object
ball.name = "Ball"
```

### eval_id-stack-0 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.26, location=(-2.09, 1.31, 0.63))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Ball cube on top of Marble
ball_location = (marble.location.x, marble.location.y, marble.location.z + 0.63 + 0.345)
bpy.ops.mesh.primitive_cube_add(size=0.69, location=ball_location)
ball = bpy.context.active_object
ball.name = "Ball"
```

### eval_id-next_to-1 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Ball cube
bpy.ops.mesh.primitive_cube_add(size=1.84, location=(-2.74, -2.86, 0.92))
ball = bpy.context.active_object
ball.name = "Ball"

# Create Pillar sphere touching Ball on -X side
pillar_location = (ball.location.x - 0.92 - 0.53, ball.location.y, 0.53)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.53, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-next_to-1 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Ball cube
bpy.ops.mesh.primitive_cube_add(size=1.84, location=(-2.74, -2.86, 0.92))
ball = bpy.context.active_object
ball.name = "Ball"

# Create Pillar UV sphere touching Ball on -X side
pillar_location = (ball.location.x - 0.92 - 0.53, ball.location.y, 0.53)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.53, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-next_to-1 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create "Ball" cube
bpy.ops.mesh.primitive_cube_add(size=1.84, location=(-2.74, -2.86, 0.92))
ball = bpy.context.active_object
ball.name = "Ball"

# Create "Pillar" UV sphere touching "Ball" on -X side
pillar_location = (ball.location.x - 0.92 - 0.53, ball.location.y, 0.53)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.53, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-next_to-1 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Ball cube
bpy.ops.mesh.primitive_cube_add(size=1.84, location=(-2.74, -2.86, 0.92))
ball = bpy.context.active_object
ball.name = "Ball"

# Create Pillar UV sphere touching Ball on -X side
pillar_location = (ball.location.x - 0.92 - 0.53, ball.location.y, 0.53)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.53, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-next_to-1 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Ball cube
bpy.ops.mesh.primitive_cube_add(size=1.84, location=(-2.74, -2.86, 0.92))
ball = bpy.context.active_object
ball.name = "Ball"

# Create Pillar sphere touching Ball on -X side
pillar_location = (ball.location.x - 0.92 - 0.53, ball.location.y, 0.53)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.53, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-next_to-1 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create the Ball cube
bpy.ops.mesh.primitive_cube_add(size=1.84, location=(-2.74, -2.86, 0.92))
ball = bpy.context.active_object
ball.name = "Ball"

# Create the Pillar sphere touching Ball on -X side
pillar_location = (ball.location.x - 0.92 - 0.53, ball.location.y, 0.53)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.53, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-next_to-1 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Ball cube
bpy.ops.mesh.primitive_cube_add(size=1.84, location=(-2.74, -2.86, 0.92))
ball = bpy.context.active_object
ball.name = "Ball"

# Create Pillar sphere touching Ball on -X side
pillar_location = (ball.location.x - 0.92 - 0.53, ball.location.y, 0.53)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.53, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-next_to-1 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Ball cube
bpy.ops.mesh.primitive_cube_add(size=1.84, location=(-2.74, -2.86, 0.92))
ball = bpy.context.active_object
ball.name = "Ball"

# Create Pillar UV sphere touching Ball on -X side
pillar_location = (ball.location.x - 0.92 - 0.53, ball.location.y, 0.53)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.53, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-stack-2 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.09, location=(-0.93, -1.02, 0.545))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Pillar cube on top of Marble
pillar_location = (marble.location.x, marble.location.y, marble.location.z + 0.545 + 0.385)
bpy.ops.mesh.primitive_cube_add(size=0.77, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-stack-2 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.09, location=(-0.93, -1.02, 0.545))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Pillar cube on top of Marble
pillar_location = (marble.location.x, marble.location.y, marble.location.z + 0.545 + 0.385)
bpy.ops.mesh.primitive_cube_add(size=0.77, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-stack-2 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.09, location=(-0.93, -1.02, 0.545))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Pillar cube on top of Marble
pillar_location = (marble.location.x, marble.location.y, marble.location.z + 0.545 + 0.385)
bpy.ops.mesh.primitive_cube_add(size=0.77, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

### eval_id-stack-2 reward=1.00 

```python
import bpy

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Marble cube
bpy.ops.mesh.primitive_cube_add(size=1.09, location=(-0.93, -1.02, 0.545))
marble = bpy.context.active_object
marble.name = "Marble"

# Create Pillar cube on top of Marble
pillar_location = (marble.location.x, marble.location.y, marble.location.z + 0.545 + 0.385)
bpy.ops.mesh.primitive_cube_add(size=0.77, location=pillar_location)
pillar = bpy.context.active_object
pillar.name = "Pillar"
```

