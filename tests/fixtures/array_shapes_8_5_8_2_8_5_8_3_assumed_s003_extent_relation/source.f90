program assumed_s003_extent_relation
  implicit none
  integer :: actual(-2:0,4:5)
  integer :: v(5)
  actual=37
  v=[11,12,13,14,15]
  call whole(actual)
  call shifted_lowers(actual)
  call section_case(v(1:5:2))
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S003 EXTENTS OK'
contains
  subroutine whole(x)
    integer, intent(in) :: x(:,:)
    if (any(shape(x) /= [3,2])) error stop 'S003 whole shape'
    if (size(x) /= 6) error stop 'S003 whole size'
    if (count(x == 37) /= 6) error stop 'S003 whole values'
  end subroutine whole
  subroutine shifted_lowers(x)
    integer, intent(in) :: x(-5:,7:)
    if (any(ubound(x) /= [-3,8])) error stop 'S003 upper relation'
  end subroutine shifted_lowers
  subroutine section_case(x)
    integer, intent(in) :: x(-1:)
    if (any(shape(x) /= [3])) error stop 'S003 section shape'
    if (any(ubound(x) /= [1])) error stop 'S003 section upper'
    if (any(x /= [11,13,15])) error stop 'S003 section values'
  end subroutine section_case
end program assumed_s003_extent_relation
