module bind_name_cardinality_scope
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int) :: first_value, second_value
  bind(c, name='   ') :: first_value, second_value
end module bind_name_cardinality_scope
