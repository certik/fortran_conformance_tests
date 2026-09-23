program main
  implicit none
  integer, parameter :: base = 7
  integer :: value = base * 4 + 1
  integer :: vector(2) = [base, base + 2]
  if (value /= 29) error stop
  if (any(vector /= [7,9])) error stop
  print '(a)', 'type_declaration r805 constant expression ok'
end program main
