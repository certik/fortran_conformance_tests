! rule: S19.4-010
! covers: associate-name-block-scope
program scoping_19_3_19_5_associate_scope
  implicit none
  integer :: checks
  integer :: item, target, seen
  checks = 0
  item = 99
  target = 10
  seen = -1
  associate (item => target)
    item = 303
    seen = item
  end associate
  if (target /= 303) then
    write(*,'(a)') 'SCOPE:associate_scope:target'
    error stop
  end if
  checks = checks + 1
  if (seen /= 303) then
    write(*,'(a)') 'SCOPE:associate_scope:seen'
    error stop
  end if
  checks = checks + 1
  if (item /= 99) then
    write(*,'(a)') 'SCOPE:associate_scope:outer'
    error stop
  end if
  checks = checks + 1
  if (checks /= 3) then
    write(*,'(a)') 'SCOPE:associate_scope:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 ASSOCIATE SCOPE OK'
contains
end program scoping_19_3_19_5_associate_scope
