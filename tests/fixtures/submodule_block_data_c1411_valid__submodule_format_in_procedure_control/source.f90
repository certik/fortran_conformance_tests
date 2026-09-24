module format_control_m
  implicit none
  interface
    module subroutine p(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module format_control_m
submodule (format_control_m) format_control_sm
contains
  module procedure p
    100 format(I0)
    value = 13
  end procedure p
end submodule format_control_sm
