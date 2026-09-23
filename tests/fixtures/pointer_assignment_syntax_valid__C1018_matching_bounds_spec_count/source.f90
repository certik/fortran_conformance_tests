program pointer_assignment_syntax_bounds_spec_few
  implicit none
  integer, pointer :: p(:,:)
  integer, target :: t(2:3,4:5)
  p(-4:,6:) => t
end program pointer_assignment_syntax_bounds_spec_few
