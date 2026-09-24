program expr_c1004_kind_mismatch
  use iso_fortran_env, only: int32, int64
  implicit none
  integer(int32) :: x
  x = (.true. ? 1_int32 : 2_int64)
end program expr_c1004_kind_mismatch
