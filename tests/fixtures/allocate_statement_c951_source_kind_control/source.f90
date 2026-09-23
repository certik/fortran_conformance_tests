program allocate_statement_c951_source_kind
  use, intrinsic :: iso_fortran_env, only: real32, real64
  implicit none
  real(real64), allocatable :: x
  allocate(x, source=real(1.0, real64))
end program allocate_statement_c951_source_kind
