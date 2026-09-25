program p
implicit none
type :: rec
  integer :: marker
end type rec
associate(chars => [character(len=3) ::])
  if (size(chars) /= 0) error stop 1
  if (len(chars) /= 3) error stop 2
end associate
if (size([rec ::]) /= 0) error stop 3
end program p
