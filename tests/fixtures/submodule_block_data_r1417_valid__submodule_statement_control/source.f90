module statement_control_m
  implicit none
  interface
    module subroutine p(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module statement_control_m
submodule (statement_control_m) statement_control_sm
contains
  module procedure p
    value = 18
  end procedure p
end submodule statement_control_sm
