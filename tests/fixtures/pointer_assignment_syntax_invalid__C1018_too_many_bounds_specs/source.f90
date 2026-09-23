program pointer_assignment_syntax_bounds_spec_many
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(2:4)
  p(-4:,6:) => t
end program pointer_assignment_syntax_bounds_spec_many
