program pointer_assignment_syntax_remap_few
  implicit none
  integer, pointer :: p(:,:)
  integer, target :: v(-3:2)
  p(-1:0,4:6) => v
end program pointer_assignment_syntax_remap_few
