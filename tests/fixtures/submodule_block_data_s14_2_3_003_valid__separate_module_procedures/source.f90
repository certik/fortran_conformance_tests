module separate_proc_m
  implicit none
  interface
    module subroutine ancestor_set(value)
      integer, intent(out) :: value
    end subroutine
    module function child_value() result(value)
      integer :: value
    end function
  end interface
end module separate_proc_m
submodule (separate_proc_m) separate_parent
  implicit none
  interface
    module function declared_in_submodule() result(value)
      integer :: value
    end function
  end interface
contains
  module procedure ancestor_set
    value = 42
  end procedure ancestor_set
end submodule separate_parent
submodule (separate_proc_m:separate_parent) separate_child
contains
  module procedure child_value
    value = declared_in_submodule() - 1
  end procedure child_value
  module procedure declared_in_submodule
    value = 65
  end procedure declared_in_submodule
end submodule separate_child
program separate_procedure_probe
  use separate_proc_m
  implicit none
  integer :: value
  value = -7
  call ancestor_set(value)
  if (value /= 42) error stop
  if (child_value() /= 64) error stop
  print '(a)', 'SUBMODULE SEPARATE PROCEDURES OK'
end program separate_procedure_probe
