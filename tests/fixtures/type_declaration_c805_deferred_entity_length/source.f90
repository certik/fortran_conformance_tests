program main
  implicit none
  block
    character, allocatable :: deferred*(:)
    allocate(character(len=6) :: deferred)
    deferred = 'pqrstu'
    if (len(deferred) /= 6) error stop
    if (deferred /= 'pqrstu') error stop
  end block
  print '(a)', 'type_declaration c805 deferred entity length ok'
end program main
