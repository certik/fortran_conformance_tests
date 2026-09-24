program expr_semantics_representation
  implicit none
  integer :: checks, object_value, computed_value, scalar_value
  integer :: array_value(2)
  checks=0
  object_value = 17
  if (object_value /= 17) error stop 'ESR:object'
  checks=checks+1
  computed_value = 2 + 5
  if (computed_value /= 7) error stop 'ESR:computation'
  checks=checks+1
  scalar_value = 42
  if (scalar_value /= 42) error stop 'ESR:scalar'
  checks=checks+1
  array_value = [3,5]
  if (any(shape(array_value) /= [2])) error stop 'ESR:array-shape'
  if (any(array_value /= [3,5])) error stop 'ESR:array-values'
  checks=checks+1
  if (checks /= 4) error stop 'ESR:checks'
  write(*,'(a)') 'EXPRESSIONS SEMANTICS REPRESENTATION OK'
end program expr_semantics_representation
