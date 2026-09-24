program attributes_contiguous_assumed_rank
  implicit none
  integer :: a(2,3)
  integer :: checks
  a = reshape([11, 13, 17, 19, 23, 29], shape(a))
  checks = 0
  call check_effective(a)
  call expect_equal(checks, 5, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES CONTIGUOUS ASSUMED RANK OK'
contains
  subroutine check_effective(x)
    integer, intent(in) :: x(..)
    call expect_logical(is_contiguous(x), .true., 'assumed-rank contiguous effective')
    call expect_equal(rank(x), 2, 'assumed-rank rank')
    call expect_equal(size(x), 6, 'assumed-rank size')
    select rank (r => x)
    rank (2)
      call expect_equal(r(1,1), 11, 'payload first')
      call expect_equal(r(2,3), 29, 'payload last')
    rank default
      error stop 'ATTR-CONTIG-AR:wrong-rank'
    end select
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-CONTIG-AR-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_logical(observed, expected, label)
    logical, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed .neqv. expected) then
      write(*,'(a,1x,a)') 'ATTR-CONTIG-AR-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_contiguous_assumed_rank
