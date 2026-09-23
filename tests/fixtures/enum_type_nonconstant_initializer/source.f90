program enum_type_nonconstant_initializer
  implicit none
  integer :: seed = 4
  enum, bind(c)
    enumerator :: first = seed
  end enum
end program enum_type_nonconstant_initializer
