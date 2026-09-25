! rule: C1550
! covers: contiguous-dummy-pointer-noncontiguous-actual-negative
! evidence: effect
! standard: f2023
program c1550_contiguous_pointer_control
  implicit none
  integer :: checks = 0
  integer, target :: a(4) = [39, 40, 41, 42]
  integer, pointer :: p(:)
  p => a
  call accept_contiguous(p)
  call expect_equal(checks, 1, 'check count')
  write(*,'(a)') 'C1550 CONTIGUOUS POINTER CONTROL OK'
contains
  subroutine accept_contiguous(q)
    integer, pointer, contiguous, intent(in) :: q(:)
    call expect_equal(q(1), 39, 'contiguous first element')
  end subroutine
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'AA1552-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
