program pointer_assignment_syntax_rank_mismatch
  implicit none
  integer, pointer :: p(:)
  integer, target :: t(2:5)
  p => t
end program pointer_assignment_syntax_rank_mismatch
