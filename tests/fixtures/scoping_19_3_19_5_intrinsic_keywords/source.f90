! rule: S19.3.5-003
! covers: intrinsic-keyword-reference-site-scope
program scoping_19_3_19_5_intrinsic_keywords
  implicit none
  integer :: checks
  integer :: tsource, fsource, result_value
  logical :: mask
  checks = 0
  tsource = -701
  fsource = -702
  mask = .false.
  result_value = -703
  result_value = merge(tsource=7, fsource=9, mask=.true.)
  if (result_value /= 7) then
    write(*,'(a)') 'SCOPE:intrinsic_keywords:merge-keyword-result'
    error stop
  end if
  checks = checks + 1
  if (tsource /= -701) then
    write(*,'(a)') 'SCOPE:intrinsic_keywords:tsource-sentinel'
    error stop
  end if
  checks = checks + 1
  if (fsource /= -702) then
    write(*,'(a)') 'SCOPE:intrinsic_keywords:fsource-sentinel'
    error stop
  end if
  checks = checks + 1
  if (mask) then
    write(*,'(a)') 'SCOPE:intrinsic_keywords:mask-sentinel'
    error stop
  end if
  checks = checks + 1
  if (checks /= 4) then
    write(*,'(a)') 'SCOPE:intrinsic_keywords:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 INTRINSIC KEYWORDS OK'
contains
end program scoping_19_3_19_5_intrinsic_keywords
