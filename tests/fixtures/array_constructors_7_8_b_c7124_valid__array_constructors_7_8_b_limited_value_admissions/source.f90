module m
implicit none
type :: base
  integer :: payload
end type base
type, extends(base) :: child
  integer :: extra
end type child
contains
subroutine observe_class(x)
  class(base), intent(in) :: x
  type(base) :: local
  local%payload = 41
  associate(values => [base :: local, x])
    if (size(values) /= 2) error stop 1
    if (values(1)%payload /= 41) error stop 2
    if (values(2)%payload /= 43) error stop 3
  end associate
end subroutine observe_class
end module m
program p
use m
implicit none
type(child) :: actual
actual%payload = 43
actual%extra = 47
associate(ints => [integer :: 5, 7])
  if (size(ints) /= 2) error stop 4
  if (ints(1) /= 5) error stop 5
  if (ints(2) /= 7) error stop 6
end associate
call observe_class(actual)
end program p
