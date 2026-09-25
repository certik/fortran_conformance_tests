program assumed_s001_list_rank
  implicit none
  integer :: actual(3,2)
  actual=23
  call observe_rank(actual)
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S001 OK'
contains
  subroutine observe_rank(x)
    integer, intent(in) :: x(:,:)
    if (rank(x) /= 2) error stop 'assumed list rank'
  end subroutine observe_rank
end program assumed_s001_list_rank
