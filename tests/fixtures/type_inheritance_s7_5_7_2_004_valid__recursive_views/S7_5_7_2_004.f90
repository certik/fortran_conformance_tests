program p
implicit none
type :: root
    integer :: value
end type
type, extends(root) :: mid
    integer :: mid_marker
end type
type, extends(mid) :: leaf
    integer :: leaf_marker
end type
type(leaf) :: object
object%mid_marker = 41
object%leaf_marker = 43
object%mid%root%value = 31
if (object%root%value /= 31) error stop 1
if (object%value /= 31) error stop 2
object%value = 37
if (object%mid%root%value /= 37) error stop 3
if (object%root%value /= 37) error stop 4
if (object%mid_marker /= 41) error stop 5
if (object%leaf_marker /= 43) error stop 6
end program p
