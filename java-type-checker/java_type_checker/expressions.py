# -*- coding: utf-8 -*-

from .types import Type, NoSuchMethod
import types


class Expression(object):
    """
    AST for simple Java expressions. Note that this package deal only with compile-time types;
    this class does not actually _evaluate_ expressions.
    """

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        raise NotImplementedError(type(self).__name__ + " must implement static_type()")

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """

        raise NotImplementedError(type(self).__name__ + " must implement check_types()")


class Variable(Expression):
    """ An expression that reads the value of a variable, e.g. `x` in the expression `x + 5`.
    """

    def __init__(self, name, declared_type):
        self.name = name  #: The name of the variable
        self.declared_type = declared_type  #: The declared type of the variable (Type)

    def static_type(self):
        return self.declared_type

    def check_types(self):
        pass


class Literal(Expression):
    """ A literal value entered in the code, e.g. `5` in the expression `x + 5`.
    """

    def __init__(self, value, type):
        self.value = value  #: The literal value, as a string
        self.type = type  #: The type of the literal (Type)

    def static_type(self):
        return self.type

    def check_types(self):
        pass


class NullLiteral(Literal):
    def __init__(self):
        super().__init__("null", Type.null)

    def static_type(self):
        return Type.null


class MethodCall(Expression):
    """
    A Java method invocation, i.e. `foo.bar(0, 1, 2)`.
    """

    def __init__(self, receiver, method_name, *args):
        self.receiver = receiver
        self.receiver = receiver  #: The object whose method we are calling (Expression)
        self.method_name = method_name  #: The name of the method to call (String)
        self.args = args  #: The method arguments (list of Expressions)

    def static_type(self):
        return self.receiver.static_type().method_named(self.method_name).return_type

    def check_types(self):

        # Nonexistent methods for special types (Avoid NoSuchMethod raised by method_named function)
        if self.receiver.static_type() == Type.null:
            raise NoSuchMethod("Cannot invoke method {}() on null".format(self.method_name))

        excludes = [Type.void, Type.int, Type.double]
        if self.receiver.static_type() in excludes:
            raise JavaTypeError("Type {0} does not have methods".format(self.receiver.static_type().name))

        # Nonexistent methods
        try:
            self.receiver.static_type().method_named(self.method_name)
        except NoSuchMethod:
            raise NoSuchMethod(
                "{0} has no method named {1}".format(
                    self.receiver.static_type().name,
                    self.method_name)
            )

        # Too many/few arguments
        expected_types = self.receiver.static_type().method_named(self.method_name).argument_types
        args = [x.static_type() for x in self.args]
        if len(expected_types) != len(args):
            raise JavaTypeError(
                "Wrong number of arguments for {0}.{1}(): expected {2}, got {3}".format(
                    self.receiver.static_type().name,
                    self.method_name,
                    len(expected_types),
                    len(args))
            )

        # Wrong argument type (also check for null)

        for i in range(len(expected_types)):
            if (not args[i].is_subtype_of(expected_types[i])) or (args[i] == Type.null and expected_types[i] in excludes):
                raise JavaTypeError(
                    "{0}.{1}() expects arguments of type {2}, but got {3}".format(
                        self.receiver.static_type().name,
                        self.method_name,
                        names(expected_types),
                        names(args))
                )

        # Deep expression
        for arg in self.args:
            arg.check_types()



class ConstructorCall(Expression):
    """
    A Java object instantiation, i.e. `new Foo(0, 1, 2)`.
    """

    def __init__(self, instantiated_type, *args):
        self.instantiated_type = instantiated_type  #: The type to instantiate (Type)
        self.args = args  #: Constructor arguments (list of Expressions)

    def static_type(self):
        return self.instantiated_type

    def check_types(self):

        # Deep expression
        for arg in self.args:
            arg.check_types()

        # Cannot instantiate primitives
        excludes = [Type.void, Type.int, Type.double, Type.null]
        if self.instantiated_type in excludes:
            raise JavaTypeError("Type {0} is not instantiable".format(self.instantiated_type.name))

        expected_types = self.instantiated_type.constructor.argument_types
        args = [x.static_type() for x in self.args]

        # Wrong number of arguments
        if len(args) != len(expected_types):
            raise JavaTypeError(
                "Wrong number of arguments for {0} constructor: expected {1}, got {2}".format(
                    self.instantiated_type.name,
                    len(expected_types),
                    len(args)))

        # Wrong argument types (also check for null)
        checkList = [True for i, j in zip(args, expected_types) if
                     (i == j or (i == Type.null and j not in excludes))]

        if len(checkList) != len(args):
            raise JavaTypeError("{0} constructor expects arguments of type {1}, but got {2}".format(
                self.instantiated_type.name,
                names(expected_types),
                names(args)))



class JavaTypeError(Exception):
    """ Indicates a compile-time type error in an expression.
    """
    pass


def names(named_things):
    """ Helper for formatting pretty error messages
    """
    return "(" + ", ".join([e.name for e in named_things]) + ")"
