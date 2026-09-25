program p
implicit none
type, abstract :: base
  integer :: payload
end type base
type, extends(base) :: child
  integer :: extra
end type child
type(child) :: left, right
left%payload = 17
left%extra = 19
right%payload = 23
right%extra = 29
associate(values => [left, right])
  if (size(values) /= 2) error stop 1
  if (values(1)%payload /= 17) error stop 2
  if (values(1)%extra /= 19) error stop 3
  if (values(2)%payload /= 23) error stop 4
  if (values(2)%extra /= 29) error stop 5
end associate
end program p
