program main_local
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int), bind(c) :: bound_value
  bound_value=1_c_int
end program main_local
