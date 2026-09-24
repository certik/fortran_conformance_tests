module relation_root_m
  implicit none
  interface
    module function child_value() result(value)
      integer :: value
    end function
  end interface
end module relation_root_m
module relation_left_m
  implicit none
  interface
    module function left_value() result(value)
      integer :: value
    end function
  end interface
end module relation_left_m
module relation_right_m
  implicit none
  interface
    module function right_value() result(value)
      integer :: value
    end function
  end interface
end module relation_right_m
submodule (relation_root_m) relation_parent
contains
end submodule relation_parent
submodule (relation_root_m:relation_parent) relation_child
contains
  module procedure child_value
    value = 41
  end procedure child_value
end submodule relation_child
submodule (relation_left_m) impl
contains
  module procedure left_value
    value = 14
  end procedure left_value
end submodule impl
submodule (relation_right_m) impl
contains
  module procedure right_value
    value = 23
  end procedure right_value
end submodule impl
program submodule_relationship_probe
  use relation_root_m
  use relation_left_m
  use relation_right_m
  implicit none
  if (child_value() /= 41) error stop
  if (left_value() /= 14) error stop
  if (right_value() /= 23) error stop
  print '(a)', 'SUBMODULE RELATIONSHIPS OK'
end program submodule_relationship_probe
