program component_dimension_shape
implicit none
type :: record
  integer, dimension(3) :: shared
  integer, dimension(3) :: overridden(2)
  integer :: explicit(-1:1)
end type
type(record) :: item
item%shared = 0
item%overridden = 0
item%explicit = 0
if (size(item%shared) /= 3) error stop 1
if (lbound(item%shared,1) /= 1 .or. ubound(item%shared,1) /= 3) error stop 2
if (size(item%overridden) /= 2) error stop 3
if (lbound(item%explicit,1) /= -1 .or. ubound(item%explicit,1) /= 1) error stop 4
print '(a)', 'COMPONENTS 7.5.4B DIMENSION OK'
end program
