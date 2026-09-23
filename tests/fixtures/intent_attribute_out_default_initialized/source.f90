program p
implicit none
type box
  integer :: stamp = 41
  integer :: payload
end type box
type(box) :: actual
actual%stamp = 17
actual%payload = 19
call observe_out_default(actual)
if (actual%stamp /= 41) error stop 1
if (actual%payload /= 23) error stop 2
write(*,'(a)') 'INTENT ATTRIBUTE OUT DEFAULT INITIALIZED OK'
contains
subroutine observe_out_default(x)
  type(box), intent(out) :: x
  if (x%stamp /= 41) error stop 3
  x%payload = 23
end subroutine
end program p
