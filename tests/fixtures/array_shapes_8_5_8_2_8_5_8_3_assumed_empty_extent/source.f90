program assumed_s003_empty_extent
  implicit none
  integer :: empty(5:3,-2:1)
  call observe_empty_shape(empty)
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S003 EMPTY OK'
contains
  subroutine observe_empty_shape(x)
    integer, intent(in) :: x(:,:)
    if (rank(x) /= 2) error stop 'S003 empty rank'
    if (any(shape(x) /= [0,4])) error stop 'S003 empty shape'
    if (size(x) /= 0) error stop 'S003 empty size'
  end subroutine observe_empty_shape
end program assumed_s003_empty_extent
