program pointer_assignment_syntax_type_mismatch
  implicit none
  integer, pointer :: p
  integer, target :: t
  p => t
end program pointer_assignment_syntax_type_mismatch
