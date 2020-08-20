import math
from numbers import Number
import pygame


def rot_center(image, angle):
    """rotate an image while keeping its center and size"""
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image


class Vector2D:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vector2D):
            x = self.x + other.x
            y = self.y + other.y
            return Vector2D(x, y)
        elif isinstance(other, Number):
            x = self.x + other
            y = self.y + other
            return Vector2D(x, y)
        else:
            raise TypeError("Other must be a scalar or Vector2D")

    def __sub__(self, other):
        if isinstance(other, Vector2D):
            x = self.x - other.x
            y = self.y - other.y
            return Vector2D(x, y)
        elif isinstance(other, Number):
            x = self.x - other
            y = self.y - other
            return Vector2D(x, y)
        else:
            raise TypeError("Other must be a scalar or Vector2D")

    def __iadd__(self, other):
        if isinstance(other, Vector2D):
            self.x += other.x
            self.y += other.y
            return self
        elif isinstance(other, Number):
            self.x += other
            self.y += other
            return self
        else:
            raise TypeError("Other must be a scalar or Vector2D")

    def __isub__(self, other):
        if isinstance(other, Vector2D):
            self.x -= other.x
            self.y -= other.y
            return self
        elif isinstance(other, Number):
            self.x -= other
            self.y -= other
            return self
        else:
            raise TypeError("Other must be a scalar or Vector2D")

    def __eq__(self, other):
        if isinstance(other, Vector2D):
            return (self.x == other.x) and (self.y == other.y)
        elif isinstance(other, list):
            return (self.x == other[0]) and (self.y == other[1])
        else:
            return False

    def __neg__(self):
        return Vector2D(-self.x, -self.y)

    # Scalar operations, other must be a scalar
    def __mul__(self, other):
        if not isinstance(other, Number):
            raise TypeError("Other must be a scalar")
        return Vector2D(other * self.x, other * self.y)

    def __truediv__(self, other):
        if not isinstance(other, Number):
            raise TypeError("Other must be a scalar")
        return Vector2D(self.x / other, self.y / other)

    def __rmul__(self, other):
        if not isinstance(other, Number):
            raise TypeError("Other must be a scalar")
        return Vector2D(other * self.x, other * self.y)

    def __str__(self):
        return str([self.x, self.y])

    def __repr__(self):
        return str([self.x, self.y])

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def angle(self):
        """
        Returns the angle, measured as 0 radians from x-axis, in radians
        """

        if self.x == 0:
            return math.pi/2 if self.y > 0 else -math.pi/2

        if self.y == 0:
            return 0 if self.x > 0 else math.pi

        angle = math.atan2(self.y, self.x)

        return angle

    def __iter__(self):
        return [self.x, self.y].__iter__()

    def dot(self, other):
        if isinstance(other, Vector2D):
            return self.x*other.x + self.y*other.y
        else:
            raise TypeError("Other must be a Vector2D")

    def copy(self):
        return Vector2D(self.x, self.y)

    @staticmethod
    def create_from_angle(angle, length):
        """
        Creates a vector according to the angle and length of the vector.
        Angle: an angle in radians, where the angle is measured from 0 on the x-axis,
        and angle goes from -180 (on the bottom) to +180 (on the top).
        Length: must be a scalar number
        """
        # convert to radians
        x = length * math.cos(angle)
        y = length * math.sin(angle)
        return Vector2D(x, y)

    @staticmethod
    def zero():
        return Vector2D(0, 0)

    @staticmethod
    def angle_between(v1, v2):
        """
        Finds the angle of v2 w.r.t to v1.
        :param v1: Reference vector to measure angle to
        :param v2: Vector to measure angle of w.r.t v1
        :return: Angle between the two vectors where v1 is the reference axis,
        0 means they point in the same direction,
        -pi means v2 points to the east of v1 (north), etc.
        0 is returned if either is a zero vector.
        """
        if v1 == Vector2D.zero() or v2 == Vector2D.zero():
            return 0
        # Use dot product to find angle
        angle = math.acos(Vector2D.dot(v1, v2) / (v1.length() * v2.length()))

        v1_angle = v1.angle()
        v2_angle = v2.angle()

        if v1_angle >= 0:
            if v2_angle < v1_angle:
                return -angle if v2_angle > v1_angle - math.pi else angle
            else:
                return angle
        else:
            if v2_angle > v1_angle:
                return angle if v2_angle <= v1_angle + math.pi else -angle
            else:
                return -angle

    @staticmethod
    def reflect(v, axis):
        """
        Reflects v across axis
        :param v: Vector to reflect
        :param axis: Axis across which to reflect v
        :return: A new vector which is v reflected across axis
        """
        if axis == Vector2D.zero():
            return v

        angle_to_axis = Vector2D.angle_between(axis, v)
        new_angle = v.angle() - 2 * angle_to_axis
        return Vector2D.create_from_angle(new_angle, v.length())

    def tuple(self):
        return (self.x, self.y)

    def unit_vector(self):
        return self / self.length()


class Vector3D:

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        if isinstance(other, Vector3D):
            x = self.x + other.x
            y = self.y + other.y
            z = self.z + other.z
            return Vector3D(x, y, z)
        elif isinstance(other, Number):
            x = self.x + other
            y = self.y + other
            z = self.z + other
            return Vector3D(x, y, z)
        else:
            raise TypeError("Other must be a scalar or Vector3D")

    def __sub__(self, other):
        if isinstance(other, Vector3D):
            x = self.x - other.x
            y = self.y - other.y
            z = self.z - other.z
            return Vector3D(x, y, z)
        elif isinstance(other, Number):
            x = self.x - other
            y = self.y - other
            z = self.z - other
            return Vector3D(x, y, z)
        else:
            raise TypeError("Other must be a scalar or Vector3D")

    def __iadd__(self, other):
        if isinstance(other, Vector3D):
            self.x += other.x
            self.y += other.y
            self.z += other.z
            return self
        elif isinstance(other, Number):
            self.x += other
            self.y += other
            self.z += other
            return self
        else:
            raise TypeError("Other must be a scalar or Vector3D")

    def __isub__(self, other):
        if isinstance(other, Vector3D):
            self.x -= other.x
            self.y -= other.y
            self.z -= other.z
            return self
        elif isinstance(other, Number):
            self.x -= other
            self.y -= other
            self.z -= other
            return self
        else:
            raise TypeError("Other must be a scalar or Vector3D")

    def __eq__(self, other):
        if isinstance(other, Vector3D):
            return (self.x == other.x) and (self.y == other.y) and (self.z == other.z)
        elif isinstance(other, list):
            return (self.x == other[0]) and (self.y == other[1]) and (self.z == other[2])
        else:
            return False

    def __neg__(self):
        return Vector3D(-self.x, -self.y, -self.z)

    # Scalar operations, other must be a scalar
    def __mul__(self, other):
        if not isinstance(other, Number):
            raise TypeError("Other must be a scalar")
        return Vector3D(other * self.x, other * self.y, other * self.z)

    def __div__(self, other):
        if not isinstance(other, Number):
            raise TypeError("Other must be a scalar")
        return Vector3D(self.x.__truediv__(other), self.y.__truediv__(other), self.z.__truediv__(other))

    def __rmul__(self, other):
        if not isinstance(other, Number):
            raise TypeError("Other must be a scalar")
        return Vector3D(other * self.x, other * self.y, other * self.z)

    def __str__(self):
        return str([self.x, self.y, self.z])

    def __repr__(self):
        return str([self.x, self.y, self.z])

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def __iter__(self):
        return [self.x, self.y, self.z].__iter__()

    def dot(self, other):
        if isinstance(other, Vector3D):
            return self.x*other.x + self.y*other.y + self.z*other.z
        else:
            raise TypeError("Other must be a Vector2D")

    def cross(self, other):
        if isinstance(other, Vector3D):
            return Vector3D(self.y*other.z - self.z*other.y, self.z*other.x - self.x*other.z, self.x*other.y - self.y*other.x)
        else:
            raise TypeError("Other must be a Vector2D")

    @staticmethod
    def zero():
        return Vector3D(0, 0, 0)
