program expr_value_characteristics
  implicit none
  integer :: checks
  checks=0
  if (kind(40+2) /= kind(1)) error stop 'EVC:integer-kind'
  checks=checks+1
  if (len('ab'//'cde') /= 5) error stop 'EVC:character-len'
  checks=checks+1
  if (rank(21+1) /= 0) error stop 'EVC:scalar-rank'
  checks=checks+1
  if (any(shape([8,13]) /= [2])) error stop 'EVC:array-shape'
  checks=checks+1
  if (checks /= 4) error stop 'EVC:checks'
  write(*,'(a)') 'EXPRESSIONS VALUE CHARACTERISTICS OK'
end program expr_value_characteristics
