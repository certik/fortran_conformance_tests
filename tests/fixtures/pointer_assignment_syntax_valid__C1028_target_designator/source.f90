program pointer_assignment_syntax_non_target
  implicit none
  integer, pointer :: p
  integer, target :: t
  p => t
end program pointer_assignment_syntax_non_target
