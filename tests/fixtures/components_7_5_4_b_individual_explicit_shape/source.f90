program component_explicit_shape
implicit none
type :: record
  integer :: explicit(-1:1)
end type
type(record) :: item
item%explicit = 0
item%explicit(-1) = 11
item%explicit(0) = 13
item%explicit(1) = 17
if (size(item%explicit) /= 3) error stop 1
if (lbound(item%explicit,1) /= -1 .or. ubound(item%explicit,1) /= 1) error stop 2
if (item%explicit(-1) /= 11) error stop 3
if (item%explicit(0) /= 13) error stop 4
if (item%explicit(1) /= 17) error stop 5
print '(a)', 'COMPONENTS 7.5.4B EXPLICIT SHAPE OK'
end program
