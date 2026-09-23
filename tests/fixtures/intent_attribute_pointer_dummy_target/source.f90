program p
implicit none
integer, target :: target
integer, target :: other
integer, pointer :: actual
target = 71
other = 82
actual => target
call define_pointer_dummy_target(actual, target)
if (.not. associated(actual, target)) error stop 1
if (associated(actual, other)) error stop 2
if (target /= 13) error stop 3
write(*,'(a)') 'INTENT ATTRIBUTE POINTER DUMMY TARGET OK'
contains
subroutine define_pointer_dummy_target(p, original)
  integer, pointer, intent(in) :: p
  integer, target, intent(inout) :: original
  if (.not. associated(p, original)) error stop 4
  p = 13
  if (.not. associated(p, original)) error stop 5
end subroutine
end program p
