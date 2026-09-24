module r1416_m
  implicit none
  interface
    module subroutine implemented(value)
      integer, intent(out) :: value
    end subroutine
    module subroutine unimplemented(value)
      integer, intent(out) :: value
    end subroutine
  end interface
end module r1416_m
submodule (r1416_m) minimal_r1416
end submodule minimal_r1416
submodule (r1416_m) full_r1416
  implicit none
  integer, parameter :: k = 8
contains
  module procedure implemented
    value = k + 7
  end procedure implemented
end submodule full_r1416
program r1416_probe
  use r1416_m
  implicit none
  integer :: value
  value = -8
  call implemented(value)
  if (value /= 15) error stop
  print '(a)', 'SUBMODULE R1416 FORMS OK'
end program r1416_probe
