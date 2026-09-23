program pointer_assignment_syntax_vector_subscript
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(5)
  p => t(1:3)
end program pointer_assignment_syntax_vector_subscript
