! rule: S9.7.3.2-004
! covers: function-result-retains-status
! The function result is proved allocated and defined before END; the caller observes the retained value.
program dealloc_function_result_retains
  implicit none
  integer, allocatable :: got(:)
  integer :: checks
  checks = 0

  got = make_result()
  if (.not. allocated(got)) error stop 'D9732:function-result:caller-allocated'
  checks = checks + 1
  if (size(got) /= 3) error stop 'D9732:function-result:caller-size'
  checks = checks + 1
  if (any(got /= [97, 101, 103])) error stop 'D9732:function-result:caller-values'
  checks = checks + 1
  if (checks /= 3) error stop 'D9732:function-result:check-total'
  write(*,'(a)') 'DEALLOC FUNCTION RESULT RETAINS OK'
contains
  function make_result() result(r)
    integer, allocatable :: r(:)
    allocate(r(-5:-3))
    r = [97, 101, 103]
    if (.not. allocated(r)) error stop 'D9732:function-result:result-allocated'
    if (lbound(r,1) /= -5) error stop 'D9732:function-result:result-lower'
    if (ubound(r,1) /= -3) error stop 'D9732:function-result:result-upper'
    if (any(r /= [97, 101, 103])) error stop 'D9732:function-result:result-values'
  end function make_result
end program dealloc_function_result_retains
