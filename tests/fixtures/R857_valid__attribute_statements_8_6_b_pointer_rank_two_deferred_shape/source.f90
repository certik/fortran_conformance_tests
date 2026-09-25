program main
  implicit none
  integer, target :: target_matrix(2,2)
  integer :: p
  pointer :: p(:,:)
  target_matrix = reshape([11, 12, 13, 14], [2, 2])
  p => target_matrix
  if (.not. associated(p, target_matrix)) error stop 1
  if (rank(p) /= 2) error stop 2
  if (size(p) /= 4) error stop 3
  if (p(2,2) /= 14) error stop 4
  write(*,'(a)') 'ATTRIBUTE STATEMENTS POINTER RANK TWO DEFERRED SHAPE OK'
end program
