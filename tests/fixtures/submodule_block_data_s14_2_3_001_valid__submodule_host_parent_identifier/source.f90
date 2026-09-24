module host_assoc_m
  implicit none
  integer, parameter :: module_base = 17
  interface
    module subroutine module_host_value(value)
      integer, intent(out) :: value
    end subroutine
    module function parent_host_value() result(value)
      integer :: value
    end function
  end interface
end module host_assoc_m
submodule (host_assoc_m) host_parent
  implicit none
  integer, parameter :: parent_base = 30
contains
  module procedure module_host_value
    value = module_base + 5
  end procedure module_host_value
end submodule host_parent
submodule (host_assoc_m:host_parent) host_child
contains
  module procedure parent_host_value
    value = parent_base + 11
  end procedure parent_host_value
end submodule host_child
program host_association_probe
  use host_assoc_m
  implicit none
  integer :: value
  value = -99
  call module_host_value(value)
  if (value /= 22) error stop
  if (parent_host_value() /= 41) error stop
  print '(a)', 'SUBMODULE HOST ASSOCIATION OK'
end program host_association_probe
