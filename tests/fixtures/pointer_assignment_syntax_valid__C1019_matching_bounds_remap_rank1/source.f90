program pointer_assignment_syntax_remap_many
  implicit none
  integer, pointer :: p(:)
  integer, target :: v(-3:2)
  p(-1:4) => v
end program pointer_assignment_syntax_remap_many
