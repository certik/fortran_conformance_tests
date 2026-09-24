program expr_c1004_type_mismatch
  implicit none
  integer :: x
  x = (.true. ? 1 : 2.0)
end program expr_c1004_type_mismatch
