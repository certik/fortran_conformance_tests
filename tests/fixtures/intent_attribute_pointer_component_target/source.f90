program p
implicit none
type pointer_box
  integer, pointer :: p
end type pointer_box
type(pointer_box) :: actual
integer, target :: target
integer, target :: other
target = 70
other = 80
actual%p => target
call define_pointer_component_target(actual, target)
if (.not. associated(actual%p, target)) error stop 1
if (associated(actual%p, other)) error stop 2
if (target /= 90) error stop 3
write(*,'(a)') 'INTENT ATTRIBUTE POINTER COMPONENT TARGET OK'
contains
subroutine define_pointer_component_target(x, original)
  type(pointer_box), intent(in) :: x
  integer, target, intent(inout) :: original
  if (.not. associated(x%p, original)) error stop 4
  x%p = 90
  if (.not. associated(x%p, original)) error stop 5
end subroutine
end program p
