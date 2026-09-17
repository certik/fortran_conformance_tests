module placement_host
  implicit none
contains
  subroutine contained_local()
    use, intrinsic :: iso_c_binding, only: c_int
    implicit none
    integer(c_int) :: bound_value
    bound_value=1_c_int
  end subroutine contained_local
end module placement_host
