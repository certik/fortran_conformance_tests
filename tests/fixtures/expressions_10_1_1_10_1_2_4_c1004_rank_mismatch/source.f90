program expr_c1004_rank_mismatch
  implicit none
  integer :: x
  x = (.true. ? 1 : [2])
end program expr_c1004_rank_mismatch
