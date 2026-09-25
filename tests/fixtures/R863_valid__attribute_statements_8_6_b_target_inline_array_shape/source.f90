program main
  implicit none
  integer :: values, matrix
  target :: values(3), matrix(0:1,2)
  values = [1, 2, 3]
  matrix = reshape([11, 12, 13, 14], [2, 2])
  if (rank(values) /= 1) error stop 1
  if (size(values) /= 3) error stop 2
  if (values(3) /= 3) error stop 3
  if (rank(matrix) /= 2) error stop 4
  if (lbound(matrix, 1) /= 0) error stop 5
  if (ubound(matrix, 1) /= 1) error stop 6
  if (ubound(matrix, 2) /= 2) error stop 7
  if (matrix(1,2) /= 14) error stop 8
  write(*,'(a)') 'ATTRIBUTE STATEMENTS TARGET INLINE ARRAY SHAPE OK'
end program
