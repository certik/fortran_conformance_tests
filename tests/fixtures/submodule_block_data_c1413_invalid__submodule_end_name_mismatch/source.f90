module mismatch_control_m
  implicit none
  interface
    module subroutine p(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module mismatch_control_m
submodule (mismatch_control_m) sm
contains
  module procedure p
    value = 44
  end procedure p
end submodule other
